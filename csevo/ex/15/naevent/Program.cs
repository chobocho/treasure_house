// 슬라이드 p15-v14-na-event — 이벤트 처리기 붙이기와 떼기, C# 14
using System;

class Button
{
    public event Action Click;
    public void Press() => Click?.Invoke();
}

class Form
{
    public Button Ok;                       // may not be created yet
}

class Program
{
    static void Main()
    {
        Action log = () => Console.WriteLine("  clicked");
        Form ready = new Form { Ok = new Button() }, empty = new Form();
        ready.Ok?.Click += log;
        empty.Ok?.Click += log;             // no button: nothing
        ready.Ok?.Press();
        ready.Ok?.Click -= log;
        ready.Ok?.Press();                  // handler removed
        Console.WriteLine("done");
#if ASSIGN
        ready.Ok?.Click = log;              // events: += and -= only
#endif
    }
}
