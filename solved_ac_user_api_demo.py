import requests
import re
import time

def verify_baekjoon_account(username):
    """
    Verify if a Baekjoon account exists using the direct Baekjoon website URL
    
    Args:
        username (str): Baekjoon username to verify
        
    Returns:
        tuple: (exists: bool, message: str, additional_info: dict)
    """
    direct_url = f"https://www.acmicpc.net/user/{username}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        start_time = time.time()
        response = requests.get(direct_url, headers=headers)
        request_time = time.time() - start_time
        
        if response.status_code == 200:
            # Si la página contiene mensajes de error específicos, el usuario no existe
            error_messages = [
                "등록된 사용자가 없습니다",  # No registered user
                "존재하지 않는 사용자입니다"  # User does not exist
            ]
            
            for error in error_messages:
                if error in response.text:
                    return False, f"User not found (Response time: {request_time:.4f}s)", {}
            
            # Si llegamos aquí, asumimos que el usuario existe
            additional_info = {}
            
            # Intentamos extraer información básica
            try:
                # Obtener información de problemas resueltos
                solved_pattern = r'맞은 문제.*?<span class="badge">\s*(\d+)\s*</span>'
                solved_match = re.search(solved_pattern, response.text, re.DOTALL)
                if solved_match:
                    additional_info['solved_count'] = solved_match.group(1).strip()
                
                # Intentar obtener rango
                rank_pattern = r'<tr>\s*<th>순위</th>\s*<td>\s*(\d+)</td>'
                rank_match = re.search(rank_pattern, response.text, re.DOTALL)
                if rank_match:
                    additional_info['rank'] = rank_match.group(1).strip()
                
                # Verificar si se menciona el nombre de usuario
                if username.lower() in response.text.lower():
                    additional_info['username_found'] = True
            except Exception as e:
                # Si hay error en la extracción, lo ignoramos
                pass
            
            return True, f"User exists (Response time: {request_time:.4f}s)", additional_info
            
        elif response.status_code == 404:
            return False, f"User not found (Response time: {request_time:.4f}s)", {}
        else:
            return False, f"Error: Status code {response.status_code} (Response time: {request_time:.4f}s)", {}
    except Exception as e:
        return False, f"Request error: {str(e)}", {}

def get_user_info(username):
    """
    Get basic information about a Baekjoon user from direct URL
    
    Args:
        username (str): Baekjoon username
        
    Returns:
        None: Prints user information if available
    """
    exists, message, info = verify_baekjoon_account(username)
    
    if not exists:
        print(f"Error: {message}")
        return
    
    print(f"Username: {username}")
    
    if 'solved_count' in info:
        print(f"Solved problems: {info['solved_count']}")
    
    if 'rank' in info:
        print(f"Rank: {info['rank']}")
    
    return exists, info

# Example usage
if __name__ == "__main__":
    test_usernames = ["baekjoon", "jhozzel", "nonexistentuser12345", "miguelmini"]
    
    for username in test_usernames:
        print(f"\n--- Verifying username: {username} ---")
        exists, message, info = verify_baekjoon_account(username)
        
        print(f"Account exists: {exists}")
        print(message)
        
        if exists and info:
            print("User information:")
            for key, value in info.items():
                print(f"- {key}: {value}") 