// 슬라이드 p4-v3-partial-rules — 구현 없으면 대리자도 없다, C# 3.0
using System;

partial class Form
{
    partial void OnLoad();

    public void Run()
    {
        OnLoad();                        // fine: the call is removed
        Action a = OnLoad;               // no method to point at
        a();
    }
}

class App
{
    static void Main()
    {
        new Form().Run();
    }
}
