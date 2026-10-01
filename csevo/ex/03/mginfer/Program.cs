// 슬라이드 p3-v2-delegate-inference — 대리자 형식을 문맥에서, C# 2.0
using System;
using System.Collections.Generic;

class Button
{
    public event EventHandler Click;
    public void Press() { Click(this, EventArgs.Empty); }
}

class App
{
    static bool IsEven(int x) { return x % 2 == 0; }
    static string Tag(int x) { return "#" + x; }
    static void OnClick(object s, EventArgs e)
    {
        Console.WriteLine("hi");
    }

    static void Main()
    {
        List<int> xs = new List<int>(new int[] { 1, 2, 3, 4 });
        List<int> evens = xs.FindAll(IsEven);         // Predicate<int>
        List<string> tags = xs.ConvertAll<string>(Tag);
        Console.WriteLine(evens.Count + " " + tags[0]);

        Button b = new Button();
        b.Click += OnClick;                             // EventHandler
        b.Press();
    }
}
