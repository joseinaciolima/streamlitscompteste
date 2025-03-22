from models import session, Usuario
import streamlit_authenticator as stauth

senha_criptografada = stauth.Hasher(["123123"]).generate()[0]
usuario = Usuario(nome="teste1", senha=senha_criptografada, email="teste1@gmail.com", admin=True)
session.add(usuario)
session.commit()

senha_criptografada = stauth.Hasher(["123456"]).generate()[0]
usuario = Usuario(nome="teste1", senha=senha_criptografada, email="teste2@gmail.com", admin=False)
session.add(usuario)
session.commit()