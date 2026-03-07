## установка LLM c hugging face
1. docker model run hf.co/CohereLabs/tiny-aya-global
2. docker exec -it ollama-ollama-1 ollama pull hf.co/panigrah/wineberto-t5-s2s
3. docker exec -it ollama-ollama-1 ollama pull hf.co/somelier/plato-1214_gguf:Q8_0
4. docker exec -it ollama-ollama-1 ollama pull hf.co/somelier/plato-1214_gguf:Q5_K_M
5. docker exec -it ollama-ollama-1 ollama pull hf.co/somelier/plato-1214_gguf:Q4_K_M
6. docker exec -it ollama-ollama-1 ollama pull hf.co/RichardErkhov/kaytoo2022_-_gemma-2-2b-winetuned-gguf:Q8_0