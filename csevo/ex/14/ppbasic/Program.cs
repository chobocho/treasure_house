// 슬라이드 p14-v13-partialprop — partial 속성과 인덱서, C# 13.0
using System;

partial class Config
{
    // defining declarations: accessors without bodies
    public partial string Name { get; set; }
    public partial int this[int i] { get; }
}

partial class Config
{
    // implementing declarations: every accessor has a body
    private string name = "none";
    private readonly int[] slots = { 10, 20, 30 };

    public partial string Name
    {
        get => name;
        set => name = value.Trim();
    }
    public partial int this[int i] => slots[i];
}

class App
{
    static void Main()
    {
        var c = new Config();
        Console.WriteLine(c.Name);
        c.Name = "  prod  ";
        Console.WriteLine("[" + c.Name + "] " + c[1]);
    }
}
