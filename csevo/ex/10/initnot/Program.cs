// 슬라이드 p10-v9-init-not — init 을 부를 수 없는 곳, C# 9.0
using System;

class C
{
    public int X { get; init; }

    public C()
    {
        X = 1;                               // ok: constructor
        Action a = () => X = 2;              // lambda in constructor
        void Local() { X = 3; }              // local function
    }

    void Method() { X = 4; }                 // ordinary method

    static void Main()
    {
        var c = new C { X = 5 };             // ok: initializer
        c.X = 6;                             // after construction
    }
}
