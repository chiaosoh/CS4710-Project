const express = require('express')
const app = express();
app.use(express.json());

const cors=require("cors");
const corsOptions ={
   origin:'*',
   credentials:true,            //access-control-allow-credentials:true
   optionSuccessStatus:200,
}

const {PythonShell} =require('python-shell');

app.use(cors(corsOptions)) // Use this after the variable declaration


let port = 5001
app.listen(port, () => console.log('listening on port ' + port));

app.post('/game_state', (request, response) => {
    const {spawn} = require('child_process');
    var data = request.body;
    const jsonData = JSON.stringify(data);

    const model = spawn('python', ["process_game_state.py", jsonData])
    model.stdout.on('data', (data) => {
        const result = data.toString().split(',');
        const move = result[1].replace(/[')]/g, '').trim();
        //const reward = result[0] //needs to be formatted if you want to use the reward
        const ret = {move: move};
        response.json(ret);
    });
    //print error messages from python for debugging
    /*
     model.stderr.on('data', (data) => {
        console.error("Error from Python:", data.toString());
    });

    model.on('close', (code) => {
        console.log(`Python process exited with code ${code}`);
    });

    model.on('error', (error) => {
        console.error("Failed to start Python process:", error);
    });
    */

});


/*
let options = {
        mode: 'text',
        pythonOptions: ['-u'], // get print results in real-time
        //If you are having python_test.py script in same folder, then it's optional.
        args: [jsonData] //An argument which can be accessed in the script using sys.argv[1]
    };

    PythonShell.run('process_game_state.py', options, function (err, result){
          if (err) throw err;
          // result is an array consisting of messages collected
          //during execution of script.
          console.log('result: ', result.toString());
          //res.send(result.toString())
    });
 */