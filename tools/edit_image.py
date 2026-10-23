from tools import base


class EditImageTool(base.MediaTool):
    def execute(self, client, parameters):
        references = base.json_value(
            parameters.get("reference_images"), list, "Additional reference images"
        )
        if parameters.get("reference_image"):
            references = [parameters["reference_image"], *references]
        return client.edit_image(
            parameters.get("model"),
            parameters.get("prompt"),
            references,
            base.model_parameters(parameters, ("aspect_ratio", "size", "quality", "n")),
            None,
        )
