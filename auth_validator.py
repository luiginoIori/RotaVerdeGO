#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de Senha - Rota Verde
Sistema de autenticação seguro
Arquivo compilado para proteção contra edição
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta


class PasswordValidator:
    """Validador de senhas com hash seguro"""
    
    def __init__(self):
        # Hashes seguros das senhas válidas (SHA-256)
        # Para adicionar nova senha: hashlib.sha256("sua_senha".encode()).hexdigest()
        self._valid_hashes = {
            # Senha padrão: "RotaVerde2024"
            "admin": "d11731c1c03db2872d25d0e07216feee575f8c3331959f80afee75c11cba16c2",
            # Senha alternativa: "FluxoCaixa@2024"
            "user": "a624f590de259c65cfd7860e881fc54806c24308c0590e716dcd4ba662d8b429"
        }
        
        # Salt para adicionar mais segurança
        self._salt = "rota_verde_salt_2024"
        
        # Controle de tentativas
        self._max_attempts = 3
        self._lockout_time = 300  # 5 minutos
        self._failed_attempts = {}
        
    def _hash_password(self, password: str) -> str:
        """Gera hash seguro da senha com salt"""
        salted_password = password + self._salt
        return hashlib.sha256(salted_password.encode()).hexdigest()
    
    def _is_locked_out(self, ip_address: str = "default") -> bool:
        """Verifica se IP está bloqueado por muitas tentativas"""
        if ip_address in self._failed_attempts:
            attempts_info = self._failed_attempts[ip_address]
            if attempts_info["count"] >= self._max_attempts:
                lockout_until = attempts_info["locked_until"]
                if datetime.now() < lockout_until:
                    return True
                else:
                    # Reset após expirar o bloqueio
                    del self._failed_attempts[ip_address]
        return False
    
    def _record_failed_attempt(self, ip_address: str = "default"):
        """Registra tentativa de senha incorreta"""
        now = datetime.now()
        if ip_address not in self._failed_attempts:
            self._failed_attempts[ip_address] = {"count": 0, "locked_until": now}
        
        self._failed_attempts[ip_address]["count"] += 1
        
        if self._failed_attempts[ip_address]["count"] >= self._max_attempts:
            self._failed_attempts[ip_address]["locked_until"] = now + timedelta(seconds=self._lockout_time)
    
    def validate_password(self, password: str, ip_address: str = "default") -> tuple:
        """
        Valida senha fornecida
        
        Args:
            password: Senha a ser validada
            ip_address: Endereço IP para controle de tentativas
            
        Returns:
            tuple: (sucesso: bool, mensagem: str, tempo_bloqueio: int)
        """
        
        # Verifica se está bloqueado
        if self._is_locked_out(ip_address):
            attempts_info = self._failed_attempts[ip_address]
            remaining_time = (attempts_info["locked_until"] - datetime.now()).seconds
            return False, f"Muitas tentativas incorretas. Tente novamente em {remaining_time} segundos.", remaining_time
        
        # Adiciona delay para prevenir ataques de força bruta
        time.sleep(0.5)
        
        # Valida senha
        password_hash = self._hash_password(password)
        
        # Verifica se hash corresponde a alguma senha válida
        for user, valid_hash in self._valid_hashes.items():
            if secrets.compare_digest(password_hash, valid_hash):
                # Senha correta - limpa tentativas falhas
                if ip_address in self._failed_attempts:
                    del self._failed_attempts[ip_address]
                return True, f"Acesso autorizado para {user}", 0
        
        # Senha incorreta - registra tentativa
        self._record_failed_attempt(ip_address)
        attempts_remaining = self._max_attempts - self._failed_attempts[ip_address]["count"]
        
        if attempts_remaining > 0:
            return False, f"Senha incorreta. {attempts_remaining} tentativas restantes.", 0
        else:
            return False, f"Muitas tentativas incorretas. Bloqueado por {self._lockout_time} segundos.", self._lockout_time
    
    def get_password_hint(self) -> str:
        """Retorna dica sobre as senhas válidas"""
        return "Dica: Combine o nome da empresa + ano atual ou Fluxo + Caixa + @ + ano"
    
    def add_new_password(self, new_password: str, username: str = "user_new") -> str:
        """
        Gera hash para nova senha (usar apenas durante desenvolvimento)
        
        Args:
            new_password: Nova senha a ser adicionada
            username: Nome do usuário
            
        Returns:
            Hash da nova senha para adicionar ao código
        """
        password_hash = self._hash_password(new_password)
        return f'"{username}": "{password_hash}"'


def main():
    """Função principal para teste do validador"""
    validator = PasswordValidator()
    
    print("=== VALIDADOR DE SENHA - ROTA VERDE ===")
    print("Sistema de Autenticação Seguro")
    print("=" * 40)
    
    while True:
        try:
            senha = input("\nDigite a senha de acesso (ou 'quit' para sair): ").strip()
            
            if senha.lower() == 'quit':
                print("Encerrando validador...")
                break
            
            if not senha:
                print("⚠️ Senha não pode estar vazia!")
                continue
            
            # Valida senha
            sucesso, mensagem, tempo_bloqueio = validator.validate_password(senha)
            
            if sucesso:
                print(f"✅ {mensagem}")
                print("Acesso liberado ao sistema!")
                break
            else:
                print(f"❌ {mensagem}")
                if tempo_bloqueio > 0:
                    print(f"⏰ Sistema bloqueado por {tempo_bloqueio} segundos")
                    break
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Operação cancelada pelo usuário")
            break
        except Exception as e:
            print(f"❌ Erro durante validação: {e}")


if __name__ == "__main__":
    main()