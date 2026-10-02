// 슬라이드 p9-v8-proppat-type — 형식 + 속성 + 이름, C# 8.0
using System;

struct Size { public int W, H; }

class App
{
    static string Describe(object o) => o switch
    {
        string { Length: 0 } => "empty string",
        string { Length: 5 } s => "five letters: " + s,
        Size { W: 0 } => "no width",
        Size { W: var w, H: var h } when w == h => "square " + w,
        int[] { Length: var n } => "int[" + n + "]",
        null => "null",
        _ => o.GetType().Name,
    };

    static void Main()
    {
        object[] xs =
        {
            "", "hello", "hi", new Size { W = 0, H = 2 },
            new Size { W = 4, H = 4 }, new int[3], null, 1.5,
        };
        foreach (object o in xs)
            Console.WriteLine(Describe(o));
        var anon = new { Name = "kim", Age = 20 };
        Console.WriteLine(anon is { Age: 20 } ? "anon 20" : "other");
    }
}
