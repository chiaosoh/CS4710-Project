const express = require('express')
const app = express();
app.use(express.json());

const cors=require("cors");
const corsOptions ={
   origin:'*',
   credentials:true,            //access-control-allow-credentials:true
   optionSuccessStatus:200,
}

app.use(cors(corsOptions)) // Use this after the variable declaration


let port = 5001
app.listen(port, () => console.log('listening on port ' + port));

app.post('/game_state', (request, response) => {

    //console.log(request)

    const {spawn} = require('child_process');
    var data = request.body
    const jsonString = JSON.stringify(data);

    const model = spawn('python', ["process_game_state.py", data])


    model.stdout.on('data', (data) => {
       console.log(data.toString());
       //res.write(data)
    });
     model.stderr.on('data', (data) => {
        console.error("Error from Python:", data.toString());
    });

    model.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });

    model.on('error', (error) => {
        console.error("Failed to start Python process:", error);
    });


});
