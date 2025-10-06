#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Validação de Senhas - Rota Verde
Verifica se as senhas estão funcionando corretamente
"""

import hashlib
import secrets

class AuthenticationSystem:
    """Sistema de autenticação para o aplicativo"""
    
    def __init__(self):
        # Hashes das senhas (mesmo do validador)
        self._valid_hashes = {
            # Senha: "RotaVerde2024"
            "admin": "d11731c1c03db2872d25d0e07216feee575f8c3331959f80afee75c11cba16c2",
            # Senha: "FluxoCaixa@2024"  
            "user": "a624f590de259c65cfd7860e881fc54806c24308c0590e716dcd4ba662d8b429"
        }
        self._salt = "rota_verde_salt_2024"
    
    def _hash_password(self, password: str) -> str:
        """Gera hash da senha com salt"""
        salted_password = password + self._salt
        return hashlib.sha256(salted_password.encode()).hexdigest()
    
    def validate_password(self, password: str) -> tuple:
        """Valida senha e retorna (sucesso, usuário)"""
        password_hash = self._hash_password(password)
        
        for user, valid_hash in self._valid_hashes.items():
            if secrets.compare_digest(password_hash, valid_hash):
                return True, user
        
        return False, None

def main():
    """Testa as senhas"""
    print("🔐 TESTE DE VALIDAÇÃO DE SENHAS")
    print("=" * 40)
    
    auth = AuthenticationSystem()
    
    senhas_teste = [
        "RotaVerde2024",
        "FluxoCaixa@2024", 
        "senha_errada",
        "rotaverde2024",  # case sensitive
        "RotaVerde2024 ",  # com espaço
        " RotaVerde2024"   # com espaço no início
    ]
    
    for senha in senhas_teste:
        print(f"\nTestando senha: '{senha}'")
        sucesso, usuario = auth.validate_password(senha)
        
        if sucesso:
            print(f"✅ VÁLIDA - Usuário: {usuario}")
        else:
            print("❌ INVÁLIDA")
        
        # Mostra hash gerado
        hash_gerado = auth._hash_password(senha)
        print(f"Hash: {hash_gerado[:20]}...")
    
    print("\n" + "=" * 40)
    print("💡 RESUMO:")
    print("  ✅ Senhas válidas:")
    print("    • RotaVerde2024 (admin)")
    print("    • FluxoCaixa@2024 (user)")
    print("  ❌ Outras senhas são inválidas")
    print("  ⚠️ Senhas são case-sensitive")
    print("  ⚠️ Não pode ter espaços extras")

if __name__ == "__main__":
    main()