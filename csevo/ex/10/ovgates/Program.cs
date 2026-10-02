// 슬라이드 p10-v9-gates-demo — C# 9 게이트 여럿을 한 파일에, C# 9.0
using System;

class App
{
    static string Size(int n) => n switch
    {
        < 0 => "negative",                   // relational pattern
        0 or 1 => "tiny",                    // or pattern
        >= 2 and <= 9 => "small",            // and pattern
        _ => "large",
    };

    static void Main()
    {
        object o = "text";
        if (o is not null)                   // not pattern
            Console.WriteLine(o is (string)); // parenthesized, type
        Console.WriteLine(Size(-1) + " " + Size(5));
        Func<int, int, int> first = (_, _) => 0;   // lambda discards
        Func<int, int> twice = static x => x * 2;  // static lambda
        nint size = 42;                            // native int
        Version v = new(9, 0);                     // target-typed new
        Console.WriteLine(first(1, 2) + twice(3) + size);
        Console.WriteLine(v);
    }
}
