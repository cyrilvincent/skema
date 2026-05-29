from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt

SECRET_KEY = "e3df716efcc8b8e146ad3124a9fd79cd016a2d9e3309275aaf220bb12b928417"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthService:

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def create_access_token(self, data: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


if __name__ == '__main__':
    s = AuthService()
    h = s.hash_password("toto")
    print(h)
    print(s.verify_password("toto", h))
    print(s.verify_password("toti", h))
    token = s.create_access_token({"id": 0, "toto": "titi"})
    print(token)
    d = s.decode_token(token)
    print(d)
    dt = datetime.fromtimestamp(d["exp"], tz=timezone.utc)
    print(dt)
    print(s.hash_password("EMla!t$!A$o2o6o622o51o"))
