// 슬라이드 p3-v2-anon-sig — 익명 메서드의 시그니처는 정확히, C# 2.0
using System;

delegate void Show(string s);
delegate int Calc(int x);

class App
{
    static void ShowObj(object o) { }

    static void Main()
    {
        Show a = ShowObj;                         // method group: ok
        Show b = delegate(object o) { };          // object != string
        Calc c = delegate(long x) { return 1; };  // long != int
        Calc d = delegate(int x) { return 1L; };  // long -> int
    }
}
