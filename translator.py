def translate_description(file_path):
    """
    Reads a URScript description file and translates its commands into human-friendly descriptions.
    Based on common URScript and Polyscope conventions.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    translation = []
    for line in lines:
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.lower().startswith("program"):
            desc = "Starting the overall robot program."
        elif stripped.lower().startswith("variables setup"):
            desc = "Setting up program variables."
        elif stripped.lower().startswith("robot program"):
            desc = "Executing the main robot program."
        elif stripped.lower().startswith("movej"):
            desc = "Performing a joint movement (MoveJ command)."
        elif stripped.lower().startswith("movel"):
            desc = "Performing a linear movement (MoveL command)."
        elif stripped.lower().startswith("force"):
            desc = "Executing a force-controlled motion."
        elif "3fg grip" in stripped.lower():
            desc = "Activating the gripper to pick up an object."
        elif "3fg release" in stripped.lower():
            desc = "Releasing the object from the gripper."
        elif stripped.lower().startswith("call"):
            subprog = stripped[4:].strip()
            desc = f"Calling subprogram: {subprog}."
        elif stripped.lower().startswith("wait:"):
            time = stripped[5:].strip()
            desc = f"Pausing for {time} seconds."
        elif "door" in stripped.lower():
            desc = "Performing door operation (opening or closing)."
        elif "pickobject" in stripped.lower():
            desc = "Executing object pick-up procedure."
        elif "unloadpiece" in stripped.lower():
            desc = "Executing object unloading procedure."
        elif "loadpiece" in stripped.lower():
            desc = "Executing object loading procedure."
        elif "insert" in stripped.lower():
            desc = "Performing an insertion operation."
        else:
            desc = stripped
        
        translation.append(" " * indent + desc)
    
    return translation
