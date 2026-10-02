// 슬라이드 p10-v9-pat-break — not·and·or 를 이름으로 쓰던 코드, C# 9.0
using System;

class not
{
    public override string ToString() => "a 'not' object";
}

class App
{
    const string y = null;

    static void Main()
    {
        object o = new not();
        object n = 7;
#if NOT
        // C# 8: type 'not' + new variable y; C# 9: not (constant y)
        Console.WriteLine(o is not y ? "true: " + y : "false");
#endif
#if OR
        if (n is int or) Console.WriteLine("or = " + or);
#endif
#if AND
        if (n is int and && and > 5) Console.WriteLine("and = " + and);
#endif
        Console.WriteLine(o + " " + n);
    }
}
