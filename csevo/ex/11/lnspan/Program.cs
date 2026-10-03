// 슬라이드 p11-v10-line — 확장된 #line, C# 10.0
using System;
using System.Diagnostics;

class App
{
    // file:line,column of the caller's current sequence point
    static string Where()
    {
        var f = new StackFrame(1, true);
        return $"{f.GetFileName()}:{f.GetFileLineNumber()}," +
               $"{f.GetFileColumnNumber()}";
    }

    static void Main()
    {
        Console.WriteLine("plain        " + Where());
#line 20 "page.razor"
        Console.WriteLine("#line 20     " + Where());
#line (5, 3) - (5, 40) "page.razor"
        Console.WriteLine("span         " + Where());
#line (5, 3) - (5, 40) 8 "page.razor"
        Console.WriteLine("span, 8      " + Where());
#line default
        Console.WriteLine("default      " + Where());
#if WARN
#line (9, 3) - (9, 20) 8 "page.razor"
        int unused;
#endif
    }
}
