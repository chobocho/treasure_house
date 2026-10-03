// 슬라이드 p11-v10-st-optional — 선택적 매개변수만 있는 생성자, C# 10.0
using System;

struct Tag
{
    public string Text;
    public Tag(string text = "none") { Text = text; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Tag("x").Text);
        Console.WriteLine(new Tag().Text ?? "(null)");   // ctor skipped
    }
}
