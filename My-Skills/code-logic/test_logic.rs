fn complex_logic(x: i32) -> Result<i32, String> {
    let start = check_start(x)?;

    if start > 100 {
        return Ok(start * 2);
    } else {
        println!("Low start");
    }

    let mut count = 0;
    loop {
        count += 1;
        if count > 5 {
            break;
        }
        if count == 2 {
            continue;
        }
        println!("Looping");
    }

    match count {
        1 => {
            println!("One");
        }
        2 => println!("Two"),
        _ => return Err("Too many".to_string()),
    }

    Ok(count)
}
