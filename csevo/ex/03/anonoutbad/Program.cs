// 슬라이드 p3-v2-anon-noparams — 매개변수 목록을 뺀 익명 메서드, C# 2.0
using System;

delegate void Two(int a, string b);
delegate void WithOut(out int x);

class App
{
    static void Main()
    {
        Two t = delegate { Console.WriteLine(a); };  // no 'a' here
        WithOut w = delegate { };                    // out: no
    }
}
