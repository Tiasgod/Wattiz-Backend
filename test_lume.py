from app.services.lume_service import LumeService

resposta = LumeService.chat(
    "Como posso economizar energia usando ar-condicionado?"
)

print(resposta)