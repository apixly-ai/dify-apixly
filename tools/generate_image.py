from tools import base


class GenerateImageTool(base.MediaTool):
    def execute(self, client, parameters):
        return client.generate_image(
            base.selected_model(parameters),
            parameters.get("prompt"),
            base.model_parameters(parameters, ("aspect_ratio", "size", "quality", "n")),
        )
