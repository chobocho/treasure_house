// 슬라이드 p5-v4-opt-caller — 뒤 버전: 호출자 정보와 dynamic, C# 5
using System;
using System.Runtime.CompilerServices;

class Program
{
    static void Where([CallerMemberName] string member = "(none)",
                      [CallerLineNumber] int line = 0)
    {
        Console.WriteLine(member + " line " + line);
    }

    static void Main()
    {
        Where();                  // static: the compiler fills both
        dynamic d = "dyn";
        Where(d);                 // dynamically bound call
        Where();
    }
}
