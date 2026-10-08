// 슬라이드 p1-design-del-cs — 시그니처만 맞으면 꽂힌다, C# 1.0
using System;

class Button
{
    public event EventHandler Click;
    string name;
    public Button(string name) { this.name = name; }
    public override string ToString() { return name; }
    public void PerformClick()
    {
        if (Click != null) Click(this, EventArgs.Empty);
    }
}

class Logger                       // knows nothing about dialogs
{
    public static void Log(object sender, EventArgs e)
    {
        Console.WriteLine("log: " + sender + " clicked");
    }
}

class Dialog
{
    Button ok = new Button("OK"), cancel = new Button("Cancel");
    void OnOk(object sender, EventArgs e)
    { Console.WriteLine("Dialog: accept"); }
    void OnCancel(object sender, EventArgs e)
    { Console.WriteLine("Dialog: close"); }

    static void Main()
    {
        Dialog d = new Dialog();
        d.ok.Click += new EventHandler(d.OnOk);      // one event type,
        d.cancel.Click += new EventHandler(d.OnCancel); // two methods
        d.ok.Click += new EventHandler(Logger.Log);  // another class
        d.ok.PerformClick();
        d.cancel.PerformClick();
    }
}
