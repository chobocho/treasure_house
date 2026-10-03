// 슬라이드 p11-v10-dc-order — 섞인 분해의 평가 순서, C# 10.0
using System;

class Box
{
    int x;
    public int X
    {
        get => x;
        set { Console.WriteLine($"  set X = {value}"); x = value; }
    }
}

class App
{
    static T Say<T>(string what, T value)
    {
        Console.WriteLine("  eval " + what);
        return value;
    }

    static void Main()
    {
        var box = new Box();
        int[] arr = new int[3];
        (Say("box", box).X, var name, arr[Say("index", 2)]) =
            (Say("1st", 10), Say("2nd", "ten"), Say("3rd", 30));
        Console.WriteLine($"{box.X} {name} {arr[2]}");
    }
}
