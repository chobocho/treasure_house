// 슬라이드 p4-v3-partial-rules — C# 3 의 partial 메서드 규칙, C# 3.0
using System;

partial class Form
{
    partial void OnLoad();
    partial int Count();                 // must return void
    public partial void OnShow();        // no access modifier
    partial void TryGet(out int value);  // no out parameter

    public void Run()
    {
        OnLoad();
    }
}

class App
{
    static void Main()
    {
        new Form().Run();
    }
}
