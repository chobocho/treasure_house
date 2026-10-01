// 슬라이드 p3-v2-capture-limits — ref 매개변수는 잡을 수 없다, C# 2.0
using System;

delegate int D();

class App
{
    static D ByRef(ref int n)
    {
        return delegate { return n; };         // a ref parameter
    }

    static D ByOut(out int n)
    {
        n = 1;
        return delegate { return n; };         // an out parameter
    }

    static void Main() { }
}
