UPLOAD_IMAGE_PROMPT = "Please give me the content in the screen which you think should be translated to other languages. Don't give all content, content where sentiment will be changed if translated to english, don't give me that content.  For example 'apno ka bank' should not be extracted. Extract only such data. Carefully read the data and extract. Return in JSON format where all extracted text is value of the main key as array.Main key is 'extracted_text'"

SUSHI_TEST_PROMPT = '''The Sushi Test is used to compare translated texts with the original text. The goal is to determine how accurately the key details, phrase structure, article usage, and tonality are preserved in the translation. The test is divided into four main parameters, each with a specified weightage:
        Key Details: This parameter assesses whether the essential information from the original text is retained in the translation. All significant facts and figures should be correctly translated.
        Phrase Structure: This evaluates whether the grammatical structure of phrases in the translation matches that of the original text. It specifically focuses on the proper use of conjunctions, verbs, and adverbs. If there are minor issues with conjunctions or verb usage, this can affect the readability but should not drastically alter the meaning. Capitalization should not have a big impact.
        Article Usage: This checks if articles (e.g., "a," "the") are used correctly in the translation. The correct use of articles is crucial for the clarity of the text. If the original text does not use articles or if article usage is not applicable (due to differences in languages), this parameter may receive a full score of 100%.
        Tonality: This evaluates whether the tone of the translation matches that of the original text. The tone should be consistent, whether formal, informal, or neutral.
        Scoring Method:
        For each parameter, scores are assigned based on how well the translation matches the original text.
        Each parameter will get a score out of 100
        If a parameter is not applicable due to differences between languages or contexts (e.g., article usage in a language where articles are not used), it will receive a full score of 100%.
        
        Return the following JSON: {‘key_details’: ‘’, ‘phrase_structure’:’’,’article_usage’:’’, ‘tonality’:’’}'''


BASE_TRANSLATE_INSTRUCTIONS = "STRICTLY follow the same JSON format in which the input is given."
BASE_TRANSLATE_INSTRUCTIONS += "Return this JSON only: {'translations':''}"
BASE_TRANSLATE_INSTRUCTIONS += "\n IF THE ORIGINAL ENGLISH SENTENCE IS FEW WORDS, the translation should also be equally small."
BASE_TRANSLATE_INSTRUCTIONS += "\n 1. FOLLOW THIS INSTRUCTION PROPERLY : If there are abbreviations present in the original english sentence, and if they have been translated, bring them back in english language."
BASE_TRANSLATE_INSTRUCTIONS += "\n 2. FOLLOW THIS INSTRUCTION PROPERLY : Keep numbers in english only, do not translate them. "

# LANGUAGE CODES
# ["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]