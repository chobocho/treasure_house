// 슬라이드 p1-java-wfc — J++ 의 WFC 꼴이 C# 1 에 그대로, C# 1.0
using System;

class Button
{
    public event EventHandler Click;
    public string Text;
    public Button(string text) { Text = text; }
    public void PerformClick()
    {
        if (Click != null) Click(this, EventArgs.Empty);
    }
}

class SimpleForm
{
    Button buttonOK = new Button("OK");
    Button buttonCancel = new Button("Cancel");
    void buttonOK_click(object sender, EventArgs e)
    {
        Console.WriteLine("Clicked OK");
    }
    void buttonCancel_click(object sender, EventArgs e)
    {
        Console.WriteLine("Clicked Cancel");
    }
    void InitForm()
    {
        buttonOK.Click += new EventHandler(this.buttonOK_click);
        buttonCancel.Click += new EventHandler(this.buttonCancel_click);
    }

    static void Main()
    {
        SimpleForm f = new SimpleForm();
        f.InitForm();
        f.buttonOK.PerformClick();
        f.buttonCancel.PerformClick();
    }
}
