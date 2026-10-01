// 슬라이드 p2-v1-logic — & 와 &&, bool 은 정수가 아니다, C# 1.0
using System;

class App
{
    static bool T(string s) { Console.Write(s + " "); return true; }
    static bool F(string s) { Console.Write(s + " "); return false; }

    static void Main()
    {
        Console.WriteLine("-> " + (F("a") && T("b")));   // b skipped
        Console.WriteLine("-> " + (F("a") & T("b")));    // both run
        Console.WriteLine("-> " + (T("a") || F("b")));
        Console.WriteLine("-> " + (T("a") | F("b")));
        Console.WriteLine("-> " + (T("a") ^ T("b")));
        int flags = 6;
        Console.WriteLine((flags & 2) != 0);             // parenthesise
        Console.WriteLine(Convert.ToInt32(true));
    }
}
