import json

from g4f import ChatCompletion, Provider

from .abstract_strategy import AbstractAnalysisStrategy


class ThirdPartyAIStrategy(AbstractAnalysisStrategy):
    @staticmethod
    def load_text(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Ошибка при чтении файла {file_path}: {e}") from e

    async def analyze(self,
                      pgn_data: str,
                      prompt_file_path: str = 'app/analysis/prompts/prompt1.txt',
                      model: str = "deepseek-r1",
                      verify: bool = True,
                      max_attempts: int = 4):
        prompt_text = self.load_text(prompt_file_path)

        full_prompt = f"{prompt_text}\n\nPGN:\n{pgn_data}"

        for attempt in range(max_attempts):
            try:
                response = await ChatCompletion.create_async(
                    model=model,
                    provider=Provider.Blackbox,
                    messages=[{"role": "user", "content": full_prompt}],
                    stream=False,
                )
                if "</think>" in response:
                    result = response.split("</think>", 1)[1].strip()
                else:
                    result = response.strip()

                if verify:
                    return json.loads(result)
                else:
                    return result

            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"Попытка {attempt + 1} не удалась, пробую еще раз...")
                else:
                    raise RuntimeError(f"Ошибка при вызове модели {model} после {max_attempts} попыток: {e}") from e
