// 슬라이드 p8-v7_2-rostruct — readonly struct 의 제약, C# 7.2
using System;

readonly struct Bad
{
    public long Cents;                   // a writable field
    public string Code { get; set; }     // a setter
    public event Action Changed;         // a field-like event
}

class App
{
    static void Main() { }
}
