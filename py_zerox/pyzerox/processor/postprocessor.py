# from typing import List, Dict, Any
# import litellm



# class :

# def latex_accumlator(aggregated_markdown: str, images: List[str]):
#     """
#     Accumulates the markdown and images into a latex file.
#     """
#     messages: List[Dict[str, Any]] = [
#         {
#             "role": "system",
#             "content": f""" Your will be given two inputs: 
#             - aggregated Latex for sequence of pages in a documentwith considering the following instruction. 
#             - The images of the pages in the document.

#             You should reproduce the latex to make hierarchy of titles same as the document images.
#             """
#         }
#     ]


#     messages.extend([
#         {
#             "role": "user",
#             "content": f""" Here is the given latex: \n {aggregated_markdown}"""
#         }
#     ])




#     response = litellm.acompletion(model=self.model, messages=messages, **self.kwargs)
#     ## completion response

#     return response["choices"][0]["message"]["content"]

