// 슬라이드 p3-v2-variance-value — 값 형식에는 변성이 없다, C# 2.0
using System;

delegate object MakeObj();
delegate void TakeInt(int x);

class App
{
    static int MakeInt() { return 1; }
    static void TakeObj(object o) { }

    static void Main()
    {
        MakeObj m = MakeInt;             // int -> object needs boxing
        TakeInt t = TakeObj;             // int -> object needs boxing
    }
}
