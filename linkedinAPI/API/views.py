from django.shortcuts import render, redirect
import requests
from django.http import JsonResponse

# LinkedIn App Credentials
CLIENT_ID = "77qflmr3ucp945"
CLIENT_SECRET = "WPL_AP1.Q6LdmJCOXNsU4cBg.aPZJDw=="
REDIRECT_URI = "http://127.0.0.1:8000/linkedin/callback/"
AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
PROFILE_URL = "https://api.linkedin.com/v2/me"
POST_URL = "https://api.linkedin.com/v2/ugcPosts"
COMMENT_URL = "https://api.linkedin.com/v2/comments"


def home(request):
    return render(request, 'linkedin_template.html')


def linkedin_login(request):
    """
    Redirect the user to LinkedIn's authorization page for login and permissions.
    """
    auth_url = (
        f"{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20w_member_social%20email"
    )
    return redirect(auth_url)


def linkedin_callback(request):
    """
    Handle the callback from LinkedIn and retrieve the access token.
    """
    code = request.GET.get('code')
    
    if not code:
        return JsonResponse({"error": "No authorization code provided"}, status=400)
    
    # Exchange the authorization code for an access token
    access_token = exchange_code_for_access_token(code)
    request.session['linkedin_access_token'] = access_token

    # Fetch the user's profile using the access token
    profile_data = fetch_linkedin_profile(access_token)
    
    if profile_data:
        linkedin_user_id = profile_data.get('id')
        if linkedin_user_id:
            # Save the user ID in the session
            request.session['linkedin_user_id'] = linkedin_user_id
            print(f"User ID saved in session: {linkedin_user_id}")
        else:
            print("Error: User ID not found in LinkedIn profile data")
    else:
        print("Error: Profile data not fetched from LinkedIn")

    # Debugging: Check session content after storing user ID
    print("Current session data:", request.session.items())

    # Redirect to the posts page after successful login
    return redirect('linkedin_posts')


def exchange_code_for_access_token(code):
    """
    Exchange the authorization code for an access token.
    """
    token_response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
    )
    
    if token_response.status_code == 200:
        token_data = token_response.json()
        return token_data.get("access_token")
    else:
        raise Exception(f"Failed to fetch access token: {token_response.text}")


def fetch_linkedin_profile(access_token):
    """
    Fetch the user's LinkedIn profile using the access token.
    """
    profile_response = requests.get(
        PROFILE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    
    if profile_response.status_code == 200:
        print("Fetched LinkedIn profile data:", profile_response.json())  # Debugging line
        return profile_response.json()
    else:
        print("Error fetching LinkedIn profile:", profile_response.text)  # Debugging line
        return None

def linkedin_posts(request):
    """
    Fetch user posts and allow commenting and interactions.
    """
    access_token = request.session.get('linkedin_access_token')
    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    linkedin_user_id = request.session.get('linkedin_user_id')
    if not linkedin_user_id:
        return JsonResponse({"error": "User ID not found in session"}, status=401)

    try:
        # Fetch posts
        posts_url = "https://api.linkedin.com/v2/ugcPosts"
        posts_response = requests.get(
            posts_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        posts_response.raise_for_status()
        posts_data = posts_response.json()

        # Render posts page with the posts data
        return render(request, 'linkedin_posts.html', {'posts_data': posts_data})

    except requests.exceptions.RequestException as e:
        return render(request, 'linkedin_posts.html', {'error': str(e)})


def create_post(request):
    """
    Post a new update on LinkedIn (status update).
    """
    access_token = request.session.get('linkedin_access_token')
    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    linkedin_user_id = request.session.get('linkedin_user_id')
    if not linkedin_user_id:
        return JsonResponse({"error": "User ID not found in session"}, status=401)

    if request.method == "POST":
        post_text = request.POST.get('post_text')

        post_data = {
            "author": f"urn:li:person:{linkedin_user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        post_response = requests.post(
            POST_URL,
            headers={"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0"},
            json=post_data
        )

        if post_response.status_code == 201:
            return redirect('linkedin_posts')
        else:
            return JsonResponse({"error": post_response.json()})

    return render(request, 'create_post.html')

def comment_on_post(request, post_id):
    """
    Add a comment on a specific post.
    """
    access_token = request.session.get('linkedin_access_token')
    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    linkedin_user_id = request.session.get('linkedin_user_id')
    if not linkedin_user_id:
        return JsonResponse({"error": "User ID not found in session"}, status=401)

    if request.method == "POST":
        comment_text = request.POST.get('comment')

        comment_data = {
            "author": f"urn:li:person:{linkedin_user_id}",
            "text": comment_text
        }

        comment_response = requests.post(
            COMMENT_URL,
            headers={"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0"},
            json=comment_data
        )

        if comment_response.status_code == 201:
            return redirect('linkedin_posts')
        else:
            return JsonResponse({"error": comment_response.json()})

    return render(request, 'comment_on_post.html', {'post_id': post_id})
