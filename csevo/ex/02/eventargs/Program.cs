// 슬라이드 p2-v1-eventargs — (sender, e) 관례, C# 1.0
using System;

class DownloadEventArgs : EventArgs
{
    public readonly string File;
    public readonly int Percent;
    public DownloadEventArgs(string file, int percent)
    {
        File = file;
        Percent = percent;
    }
}

delegate void DownloadEventHandler(object sender, DownloadEventArgs e);

class Downloader
{
    public string Name;
    public event DownloadEventHandler Progress;

    protected virtual void OnProgress(DownloadEventArgs e)
    {
        DownloadEventHandler h = Progress;
        if (h != null) h(this, e);
    }

    public void Run(string file)
    {
        for (int p = 50; p <= 100; p += 50)
            OnProgress(new DownloadEventArgs(file, p));
    }
}

class App
{
    static void Print(object sender, DownloadEventArgs e)
    {
        Downloader d = (Downloader)sender;          // cast back
        Console.WriteLine(d.Name + ": " + e.File + " " + e.Percent);
    }

    static void Main()
    {
        Downloader d = new Downloader();
        d.Name = "dl-1";
        d.Progress += new DownloadEventHandler(Print);
        d.Run("deck.html");
    }
}
