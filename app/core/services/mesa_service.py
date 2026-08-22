from datetime import datetime
from app.core.models import Mesa, GrupoMesa
from app.infrastructure.extensions import db


class MesaService:
    @staticmethod
    def alternar_ativa(mesa_id: int) -> bool:
        """Ativa/desativa uma mesa específica (ex.: quebrada, em manutenção),
        sem alterar a numeração nem o total de mesas do salão."""
        mesa = Mesa.query.get_or_404(mesa_id)
        if mesa.status == 'Ocupada':
            raise ValueError(f"Mesa {mesa.numero} está ocupada e não pode ser desativada.")
        mesa.ativa = not mesa.ativa
        db.session.commit()
        return mesa.ativa

    @staticmethod
    def ajustar_salao(nova_quantidade: int) -> str:
        if nova_quantidade < 0:
            raise ValueError("Quantidade de mesas não pode ser negativa.")
        mesas_atuais = Mesa.query.all()
        total_atual = len(mesas_atuais)
        if nova_quantidade > total_atual:
            for i in range(total_atual + 1, nova_quantidade + 1):
                db.session.add(Mesa(numero=str(i).zfill(2), status='Livre'))
            db.session.commit()
            return f"Salão expandido para {nova_quantidade} mesas."
        if nova_quantidade < total_atual:
            mesas_remover = Mesa.query.filter(Mesa.id > nova_quantidade).all()
            if not all(m.status == 'Livre' for m in mesas_remover):
                raise ValueError("Não é possível remover mesas ocupadas!")
            for m in mesas_remover:
                db.session.delete(m)
            db.session.commit()
            return f"Salão reduzido para {nova_quantidade} mesas."
        return "Nenhuma alteração necessária."

    @staticmethod
    def unir(mesa_ids: list, usuario_id: int) -> GrupoMesa:
        """Une as mesas informadas num só grupo (organização visual).

        Se alguma das mesas selecionadas já pertence a um grupo, as demais
        entram nesse mesmo grupo em vez de criar um novo — é assim que uma
        mesa nova se junta a uma união já existente (ex.: chegou mais gente
        e a mesa 09 precisa se juntar às mesas 03+06 que já estavam unidas).
        Se as mesas selecionadas pertencerem a grupos diferentes, todos esses
        grupos são fundidos num só (nenhuma mesa fica "órfã" de um grupo que
        deixou de existir)."""
        mesa_ids = [int(m) for m in mesa_ids]
        if len(mesa_ids) < 2:
            raise ValueError("Selecione pelo menos 2 mesas para unir.")
        mesas = Mesa.query.filter(Mesa.id.in_(mesa_ids)).all()
        if len(mesas) != len(set(mesa_ids)):
            raise ValueError("Uma ou mais mesas selecionadas não foram encontradas.")

        grupos_existentes = sorted({m.grupo_id for m in mesas if m.grupo_id is not None})

        if not grupos_existentes:
            grupo = GrupoMesa(criado_em=datetime.now(), criado_por_id=usuario_id)
            db.session.add(grupo)
            db.session.flush()
            for mesa in mesas:
                mesa.grupo_id = grupo.id
            db.session.commit()
            return grupo

        grupo_destino_id = grupos_existentes[0]
        outros_grupos_ids = grupos_existentes[1:]
        if outros_grupos_ids:
            Mesa.query.filter(Mesa.grupo_id.in_(outros_grupos_ids)).update(
                {'grupo_id': grupo_destino_id}, synchronize_session=False
            )
            GrupoMesa.query.filter(GrupoMesa.id.in_(outros_grupos_ids)).delete(
                synchronize_session=False
            )

        for mesa in mesas:
            mesa.grupo_id = grupo_destino_id

        db.session.commit()
        return GrupoMesa.query.get(grupo_destino_id)

    @staticmethod
    def desunir_mesa(mesa_id: int) -> None:
        """Remove apenas a mesa informada do grupo. Dissolve o grupo se sobrar <= 1 membro."""
        mesa = Mesa.query.get_or_404(mesa_id)
        grupo_id = mesa.grupo_id
        if grupo_id is None:
            return
        mesa.grupo_id = None
        db.session.flush()

        restantes = Mesa.query.filter_by(grupo_id=grupo_id).all()
        if len(restantes) <= 1:
            for m in restantes:
                m.grupo_id = None
            grupo = GrupoMesa.query.get(grupo_id)
            if grupo:
                db.session.delete(grupo)
        db.session.commit()
