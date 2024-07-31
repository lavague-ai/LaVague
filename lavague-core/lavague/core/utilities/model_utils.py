def get_model_name(llm):
    if hasattr(llm, "model"):
        return llm.model
    elif hasattr(llm, "model_name"):
        return llm.model_name
    else:
        return None
