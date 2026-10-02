// 슬라이드 p10-v9-with-shallow — with 는 얕은 복사, C# 9.0
using System;
using System.Collections.Generic;

record Team(string Name, List<string> Members);

class App
{
    static void Main()
    {
        var red = new Team("red", new List<string> { "ann" });
        var blue = red with { Name = "blue" };
        blue.Members.Add("bob");             // same list object
        Console.WriteLine(string.Join(",", red.Members));
        Console.WriteLine(ReferenceEquals(red.Members, blue.Members));
        Console.WriteLine(red == blue);
        var green = blue with { Name = "red" };
        Console.WriteLine(red == green);     // list compared by ref
    }
}
