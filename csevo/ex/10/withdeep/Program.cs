// 슬라이드 p10-v9-with-deep — 복사 생성자로 깊은 복사, C# 9.0
using System;
using System.Collections.Generic;

record Team(string Name, List<string> Members)
{
    protected Team(Team original)
    {
        Name = original.Name;
        Members = new List<string>(original.Members);
    }
}

class App
{
    static void Main()
    {
        var red = new Team("red", new List<string> { "ann" });
        var blue = red with { Name = "blue" };
        blue.Members.Add("bob");
        Console.WriteLine(string.Join(",", red.Members));
        Console.WriteLine(string.Join(",", blue.Members));
    }
}
