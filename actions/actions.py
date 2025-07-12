from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, ActionExecuted

class ActionComponenteActivo(Action):
    def name(self):
        return "action_componente_activo"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        tipo_solicitud = tracker.get_slot("tipo_solicitud") or \
                        next(tracker.get_latest_entity_values("tipo_solicitud"), None)

        if tipo_solicitud == "vacaciones":
            componente_activo = "formulario"
            mensaje = (
                "Las vacaciones son solicitudes con descuento de horas.\n"
                "Debes seleccionar los días en los que estarás ausente y la fecha en la que te reincorporarás.\n\n"
                
                "A continuación, completa el siguiente formulario. Si necesitas uno diferente, házmelo saber!"
            )
            tipo_formulario = tipo_solicitud
        elif tipo_solicitud == "permiso":
            componente_activo = "formulario"
            mensaje = (
                "Los permisos son solicitudes sin descuento de horas.\n"
                "Utilízalos para ausentarte por motivos personales, como citas médicas o asuntos familiares."
                "Ten en cuenta que si no cumples con los requisitos, el permiso podría descontar tus días libres.\n\n"
                "Completa el siguiente formulario. Si necesitas otro tipo de formulario, solo dímelo."
            )
            tipo_formulario = tipo_solicitud
        elif tipo_solicitud == "hoja de ruta":
            componente_activo = "formulario"
            mensaje = (
                "La hoja de ruta es una solicitud con descuento de horas.\n"
                "Úsala cuando necesites salir por horas de tu jornada laboral por motivos personales sin justificación."
                "Si necesitas un formulario diferente, estaré encantado de ayudarte.\n\nPor favor, completa el siguiente formulario: "
            )
            tipo_formulario = "hoja_ruta"
        else:
            componente_activo = "selector"
            mensaje = "Por favor, selecciona un tipo de solicitud válido: **vacaciones**, **permiso** o **hoja de ruta**."
            tipo_formulario = None

        dispatcher.utter_message(json_message={
            "text": mensaje,
            "componente_activo": componente_activo,
            "tipo_formulario": tipo_formulario
        })

        return [SlotSet("componente_activo", componente_activo)]

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_default")
        return [
            SlotSet("componente_activo", "selector"),
            FollowupAction("action_listen")
        ]

class ActionStop(Action):
    def name(self) -> Text:
        return "action_stop"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        return [
            SlotSet("componente_activo", None),
            SlotSet("tipo_solicitud", None),
            ActionExecuted("action_listen")  # Reinicio completo
        ]