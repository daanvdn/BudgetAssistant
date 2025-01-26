import { Component, EventEmitter, OnInit, Output, ViewChild } from '@angular/core';
import { Observable } from 'rxjs';
import { FileQueueObject, FileUploaderService } from '../file-uploader.service';




@Component({
  selector: 'file-uploader, [file-uploader]',
  templateUrl: 'file-uploader.component.html',
  styleUrls: ['./file-uploader.component.scss']
})

export class FileUploaderComponent implements OnInit {

  @Output() onCompleteItem = new EventEmitter();

  @ViewChild('fileInput') fileInput?: { nativeElement: any; };
  queue?: Observable<FileQueueObject[]>;

  constructor(public uploader: FileUploaderService) { }

  ngOnInit() {
    this.queue = this.uploader.queue;
    this.uploader.onCompleteItem = this.completeItem;
  }

  completeItem = (item: FileQueueObject, response: any) => {
    this.onCompleteItem.emit({ item, response });
  }

  addToQueue() {
    const fileBrowser = this.fileInput?.nativeElement;
    this.uploader.addToQueue(fileBrowser.files);
  }
}