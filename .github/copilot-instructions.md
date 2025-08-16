i am using powershell in vscode.
when you generate code, please provide the name of the file, including the path.
we are going to write an ai assitant that uses grog cloud to speak with llms. api keys and etc are in the .env file.
kinda a "gpt wrapper". but in future we will add speech recognition, then text to speech for it's responses, add ability to see things from the camera, etc.
this will be used for an IoT project, where we have smart inventory system.
it will be a camera mounted on the roof, that listens to everything, and when we ask smth like "hey agent, where is that green board that converts the high voltage to low voltage?"
and it should understand that the user wants to find a buck converter module, it will check the database, where it has all the items in the room and their locations,
and point where it is in the room with a laser or smth like that, and respond. if user takes something or places somethign somewhere, it should update the database.
the project should be written in such a way that we can use it on some small microcontroller or small computer like raspberry pi.
code should be efficient and maintainable.