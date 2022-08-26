import requests

def test_auth():
    resp = requests.get(
        url='localhost:8080/accounts/register',
        params={
            'phone': '+380...',
            'app_id': 424242
        })

    assert resp.code == 200

    code = input('Auth code:')

    resp = requests.post(
        url='localhost:8080/accounts/auth_code',
        data={
            'phone': '+380...',
            'auth_code': code
        })

    assert resp.code == 200
