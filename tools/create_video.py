from tools import base


class CreateVideoTool(base.MediaTool):
    def execute(self, client, parameters):
        return client.create_video(
            parameters.get("model"),
            parameters.get("prompt"),
            base.model_parameters(parameters, ("seconds", "resolution", "aspect_ratio")),
        )
