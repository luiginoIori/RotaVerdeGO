#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Hash para Senhas - Rota Verde
Script para gerar hashes corretos das senhas
"""

import hashlib

def generate_hash(password: str, salt: str = "rota_verde_salt_2024") -> str:
    """Gera hash da senha com salt"""
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()

def main():
    """Gera hashes das senhas padrão"""
    print("🔑 GERADOR DE HASH - ROTA VERDE")
    print("=" * 40)
    
    senhas = {
        "RotaVerde2024": "admin",
        "FluxoCaixa@2024": "user"
    }
    
    salt = "rota_verde_salt_2024"
    
    print(f"Salt usado: {salt}")
    print()
    
    for senha, usuario in senhas.items():
        hash_gerado = generate_hash(senha, salt)
        print(f"Senha: {senha}")
        print(f"Usuário: {usuario}")
        print(f"Hash: {hash_gerado}")
        print()
        
        # Testa o hash
        hash_teste = generate_hash(senha, salt)
        if hash_gerado == hash_teste:
            print(f"✅ Hash verificado para {senha}")
        else:
            print(f"❌ Erro na verificação do hash para {senha}")
        print("-" * 40)

if __name__ == "__main__":
    main()