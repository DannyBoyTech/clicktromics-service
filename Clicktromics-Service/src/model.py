from admet_ai import ADMETModel
ADMET_MODEL: ADMETModel | None = None


def load_admet_model() -> None:
    """Loads the models into memory."""
    global ADMET_MODEL

    ADMET_MODEL = ADMETModel()


def get_admet_model() -> ADMETModel:
    """Get the ADMET-AI model.

    :return: The ADMET-AI model.
    """
    return ADMET_MODEL