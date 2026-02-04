from app import app, db, Usuario

def criar_usuario_mestre():
    with app.app_context():
        # Procuramos se já existe esse admin específico
        admin = Usuario.query.filter_by(username='adminprosa').first()
        
        if not admin:
            usuario_zero = Usuario(
                username='adminprosa',
                senha='petiscaria2026',
                cargo='admin'
            )
            db.session.add(usuario_zero)
            db.session.commit()
            print("✅ Usuário Mestre 'adminprosa' criado com sucesso!")
        else:
            # Caso já exista, vamos apenas garantir que a senha seja a que você escolheu
            admin.senha = 'petiscaria2026'
            db.session.commit()
            print("✅ Senha do 'adminprosa' atualizada!")

if __name__ == "__main__":
    criar_usuario_mestre()