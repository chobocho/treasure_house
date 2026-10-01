// 슬라이드 p3-v2-anon-recursion — 자기를 부르는 익명 메서드, C# 2.0
using System;

delegate int F(int n);

class App
{
    static void Main()
    {
        F fact = delegate(int n)
        {
            return n <= 1 ? 1 : n * fact(n - 1);   // fact: unassigned
        };
        int x;
        F show = delegate(int n) { return n + x; }; // x: unassigned
    }
}
