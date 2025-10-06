#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para compilar o validador de senha em executável
Usa PyInstaller para criar arquivo .exe não editável
"""

import subprocess
import sys
import os


def install_pyinstaller():
    """Instala PyInstaller se não estiver disponível"""
    try:
        import PyInstaller
        print("✅ PyInstaller já está instalado")
        return True
    except ImportError:
        print("📦 Instalando PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller instalado com sucesso")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar PyInstaller: {e}")
            return False


def compile_validator():
    """Compila o validador de senha em executável"""
    
    # Verifica se arquivo fonte existe
    if not os.path.exists("auth_validator.py"):
        print("❌ Arquivo auth_validator.py não encontrado!")
        return False
    
    print("🔨 Compilando validador de senha...")
    
    try:
        # Comando PyInstaller para criar executável
        cmd = [
            "pyinstaller",
            "--onefile",                    # Arquivo único
            "--noconsole",                  # Sem janela de console (opcional)
            "--name=password_validator",    # Nome do executável
            "--distpath=.",                # Pasta de saída
            "--workpath=temp_build",       # Pasta temporária
            "--specpath=temp_build",       # Pasta spec temporária
            "auth_validator.py"
        ]
        
        # Executa compilação
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Compilação concluída com sucesso!")
            print("📁 Executável criado: password_validator.exe")
            
            # Limpa arquivos temporários
            cleanup_temp_files()
            
            return True
        else:
            print(f"❌ Erro na compilação: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ PyInstaller não encontrado. Instale com: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"❌ Erro durante compilação: {e}")
        return False


def cleanup_temp_files():
    """Remove arquivos temporários da compilação"""
    try:
        import shutil
        
        # Remove pasta temporária
        if os.path.exists("temp_build"):
            shutil.rmtree("temp_build")
            print("🧹 Arquivos temporários removidos")
            
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível limpar arquivos temporários: {e}")


def create_batch_file():
    """Cria arquivo batch para facilitar execução"""
    batch_content = '''@echo off
title Validador de Senha - Rota Verde
echo.
echo ===================================
echo  VALIDADOR DE SENHA - ROTA VERDE
echo ===================================
echo.
password_validator.exe
echo.
echo Pressione qualquer tecla para sair...
pause > nul
'''
    
    try:
        with open("executar_validador.bat", "w", encoding="utf-8") as f:
            f.write(batch_content)
        print("✅ Arquivo batch criado: executar_validador.bat")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível criar arquivo batch: {e}")


def main():
    """Função principal"""
    print("🔐 COMPILADOR DE VALIDADOR DE SENHA")
    print("==================================")
    
    # Instala PyInstaller se necessário
    if not install_pyinstaller():
        return
    
    # Compila o validador
    if compile_validator():
        create_batch_file()
        
        print("\n✅ PROCESSO CONCLUÍDO!")
        print("=" * 30)
        print("📁 Arquivos criados:")
        print("  - password_validator.exe (executável principal)")
        print("  - executar_validador.bat (facilitador)")
        print("\n💡 Instruções:")
        print("  1. Execute 'password_validator.exe' ou 'executar_validador.bat'")
        print("  2. Senhas padrão:")
        print("     - RotaVerde2024")
        print("     - FluxoCaixa@2024")
        print("  3. O executável não pode ser editado/modificado")
        print("  4. Controle de tentativas automático")
        
    else:
        print("\n❌ Falha na compilação!")
        print("Verifique os erros acima e tente novamente")


if __name__ == "__main__":
    main()